module apifast__firr10__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // ----------------------------------------------------------
    // 1. Delay line registers (10 taps: tap0 = newest = current x)
    // ----------------------------------------------------------
    reg [7:0] tap [0:9];  // tap[0] = x, tap[1] = x_prev1, ..., tap[9] = x_prev9
    
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 10; i = i + 1)
                tap[i] <= 8'd0;
        end else begin
            // Shift and insert new sample
            tap[0] <= x;
            for (i = 1; i < 10; i = i + 1)
                tap[i] <= tap[i-1];
        end
    end

    // ----------------------------------------------------------
    // 2. Multiply-accumulate pipeline stages
    //    Coefficient k+1 for tap[k]
    // ----------------------------------------------------------
    // Stage 0: multiply each tap by its coefficient (k+1)
    //          product width: 8 bits * 4 bits (max coeff 10 = 4'b1010) = 12 bits
    reg [11:0] prod [0:9];
    
    always @* begin
        for (i = 0; i < 10; i = i + 1)
            prod[i] = tap[i] * (i + 1);
    end
    
    // ----------------------------------------------------------
    // 3. Pipeline adder tree (binary reduction)
    //    Each stage adds two numbers -> reduces width slightly
    // ----------------------------------------------------------
    // Stage 1: 10 -> 5 sums (partial products)
    reg [12:0] s1 [0:4];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 5; i = i + 1)
                s1[i] <= 13'd0;
        end else begin
            s1[0] <= prod[0] + prod[1];
            s1[1] <= prod[2] + prod[3];
            s1[2] <= prod[4] + prod[5];
            s1[3] <= prod[6] + prod[7];
            s1[4] <= prod[8] + prod[9];
        end
    end
    
    // Stage 2: 5 -> 3 sums (two pairs + one leftover)
    reg [13:0] s2 [0:2];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 3; i = i + 1)
                s2[i] <= 14'd0;
        end else begin
            s2[0] <= s1[0] + s1[1];
            s2[1] <= s1[2] + s1[3];
            s2[2] <= {2'b0, s1[4]};  // zero-extend
        end
    end
    
    // Stage 3: 3 -> 2 sums
    reg [14:0] s3 [0:1];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s3[0] <= 15'd0;
            s3[1] <= 15'd0;
        end else begin
            s3[0] <= s2[0] + s2[1];
            s3[1] <= {1'b0, s2[2]};  // zero-extend
        end
    end
    
    // Stage 4: 2 -> 1 final sum (clipped to low 16 bits)
    reg [15:0] sum_final;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            sum_final <= 16'd0;
        else
            sum_final <= s3[0] + s3[1];  // saturates naturally to 15 bits, but we take low 16
    end
    
    // ----------------------------------------------------------
    // 4. Output register (already registered in final sum stage)
    // ----------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            y <= 16'd0;
        else
            y <= sum_final[15:0];
    end

endmodule
module apifast__fir6_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Delay line (6 samples, 8-bit each)
    reg [7:0] delay_line [0:5];
    integer i;

    // Coefficients: [3, 5, 7, 7, 5, 3]
    // We'll pipeline the multiply-accumulate to minimize critical path
    
    // Stage 1: Compute products (8-bit x 4-bit -> 12-bit)
    wire [11:0] prod0, prod1, prod2, prod3, prod4, prod5;
    
    // Coefficient 3 = 3 (binary 0011), 5 = 5 (0101), 7 = 7 (0111)
    assign prod0 = delay_line[0] * 8'd3;   // 3
    assign prod1 = delay_line[1] * 8'd5;   // 5
    assign prod2 = delay_line[2] * 8'd7;   // 7
    assign prod3 = delay_line[3] * 8'd7;   // 7
    assign prod4 = delay_line[4] * 8'd5;   // 5
    assign prod5 = delay_line[5] * 8'd3;   // 3

    // Pipeline registers for products
    reg [11:0] p0, p1, p2, p3, p4, p5;
    
    // Stage 2: First level of addition tree - sum pairs
    reg [12:0] sum01, sum23, sum45; // 12-bit + 12-bit = 13-bit max
    
    // Stage 3: Second level 
    reg [13:0] sum0123, sum45_ext; // 13-bit + 13-bit = 14-bit
    
    // Stage 4: Final sum and truncation
    reg [15:0] sum_all;
    
    // Shift register for delay line (updated on posedge clk)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 6; i = i + 1)
                delay_line[i] <= 8'd0;
        end else begin
            delay_line[0] <= x;
            for (i = 1; i < 6; i = i + 1)
                delay_line[i] <= delay_line[i-1];
        end
    end

    // Pipeline stage 1: register products
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p0 <= 12'd0;
            p1 <= 12'd0;
            p2 <= 12'd0;
            p3 <= 12'd0;
            p4 <= 12'd0;
            p5 <= 12'd0;
        end else begin
            p0 <= prod0;
            p1 <= prod1;
            p2 <= prod2;
            p3 <= prod3;
            p4 <= prod4;
            p5 <= prod5;
        end
    end

    // Pipeline stage 2: first additions
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum01 <= 13'd0;
            sum23 <= 13'd0;
            sum45 <= 13'd0;
        end else begin
            sum01 <= p0 + p1;
            sum23 <= p2 + p3;
            sum45 <= p4 + p5;
        end
    end

    // Pipeline stage 3: second additions
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum0123 <= 14'd0;
            sum45_ext <= 14'd0;
        end else begin
            sum0123 <= sum01 + sum23;
            sum45_ext <= sum45;  // just register for timing balance
        end
    end

    // Pipeline stage 4: final sum and output
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sum_all <= 16'd0;
            y <= 16'd0;
        end else begin
            sum_all <= sum0123 + sum45_ext;
            y <= sum_all[15:0];
        end
    end

endmodule
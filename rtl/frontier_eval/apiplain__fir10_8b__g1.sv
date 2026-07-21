module apiplain__fir10_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // Fixed coefficients
    localparam [3:0] coeff0 = 4'd3;
    localparam [3:0] coeff1 = 4'd5;
    localparam [3:0] coeff2 = 4'd7;
    localparam [3:0] coeff3 = 4'd9;
    localparam [3:0] coeff4 = 4'd11;
    localparam [3:0] coeff5 = 4'd11;
    localparam [3:0] coeff6 = 4'd9;
    localparam [3:0] coeff7 = 4'd7;
    localparam [3:0] coeff8 = 4'd5;
    localparam [3:0] coeff9 = 4'd3;

    // 10-element delay line
    reg [7:0] delay_line [9:0];
    
    // Sum of products (needs sufficient width)
    wire [19:0] sum;
    
    // Combinational sum of products
    assign sum = (delay_line[0] * coeff0) + 
                 (delay_line[1] * coeff1) + 
                 (delay_line[2] * coeff2) + 
                 (delay_line[3] * coeff3) + 
                 (delay_line[4] * coeff4) + 
                 (delay_line[5] * coeff5) + 
                 (delay_line[6] * coeff6) + 
                 (delay_line[7] * coeff7) + 
                 (delay_line[8] * coeff8) + 
                 (delay_line[9] * coeff9);

    // Sequential logic
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear delay line
            for (i = 0; i < 10; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            // Clear output
            y <= 16'd0;
        end
        else begin
            // Shift delay line and insert new sample
            delay_line[0] <= x;
            for (i = 1; i < 10; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            // Output low 16 bits of sum
            y <= sum[15:0];
        end
    end

endmodule
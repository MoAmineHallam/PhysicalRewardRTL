module apiplain__fir6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    // 6-tap delay line for past samples
    reg [7:0] delay_line [0:5];
    
    // Fixed coefficients [3, 5, 7, 7, 5, 3]
    // For unsigned 8-bit input:
    // - 3 * x = x*2 + x
    // - 5 * x = x*4 + x
    // - 7 * x = x*8 - x
    
    wire [15:0] product0;
    wire [15:0] product1;
    wire [15:0] product2;
    wire [15:0] product3;
    wire [15:0] product4;
    wire [15:0] product5;
    
    // Compute products using shifts and adds for area efficiency
    assign product0 = {delay_line[0], 1'b0} + delay_line[0];          // 3 * delay[0]
    assign product1 = {delay_line[1], 2'b00} + delay_line[1];        // 5 * delay[1]
    assign product2 = {delay_line[2], 3'b000} - delay_line[2];       // 7 * delay[2]
    assign product3 = {delay_line[3], 3'b000} - delay_line[3];       // 7 * delay[3]
    assign product4 = {delay_line[4], 2'b00} + delay_line[4];        // 5 * delay[4]
    assign product5 = {delay_line[5], 1'b0} + delay_line[5];          // 3 * delay[5]
    
    // Sum all products - need enough bits, then take low 16
    wire [18:0] sum;
    assign sum = product0 + product1 + product2 + product3 + product4 + product5;
    
    // Sequential logic for delay line and output
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Clear all state on active-low reset
            for (i = 0; i < 6; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            // Shift delay line and input new sample
            delay_line[0] <= x;
            for (i = 1; i < 6; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            
            // Registered output - take low 16 bits of sum
            y <= sum[15:0];
        end
    end

endmodule
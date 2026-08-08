module base__fir10_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] x_delay [0:9]; // create a delay line of past samples
    reg [15:0] prod_result [0:9]; // register to hold the multiplication
    reg [8:0] i;
    
    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 16'd0;
            for (i = 0; i <= 9; i = i + 1) begin
                x_delay[i] <= 8'd0;
                prod_result[i] <= 16'd0;
            end
        end
        else begin
            // shift in the new sample
            x_delay[0] <= x;
            for (i = 0; i <= 8; i = i + 1) begin
                x_delay[i+1] <= x_delay[i];
            end
            
            // calculate multiplications
            prod_result[0] <= x_delay[0]*8'd3;
            prod_result[1] <= x_delay[1]*8'd5;
            prod_result[2] <= x_delay[2]*8'd7;
            prod_result[3] <= x_delay[3]*8'd9;
            prod_result[4] <= x_delay[4]*8'd11;
            prod_result[5] <= x_delay[5]*8'd11;
            prod_result[6] <= x_delay[6]*8'd9;
            prod_result[7] <= x_delay[7]*8'd7;
            prod_result[8] <= x_delay[8]*8'd5;
            prod_result[9] <= x_delay[9]*8'd3;
            
            // sum all multiplications
            y <= prod_result[0] + prod_result[1] + prod_result[2] + prod_result[3] + prod_result[4] + prod_result[5] + prod_result[6] + prod_result[7] + prod_result[8] + prod_result[9];
        end
    end

endmodule
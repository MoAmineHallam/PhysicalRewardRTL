module base__firr6__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap0, tap1, tap2, tap3, tap4, tap5; // Delay line registers
    reg [15:0] sum; // Sum register

    always @(posedge clk, negedge rst_n) begin
        if (!rst_n) begin
            {tap0, tap1, tap2, tap3, tap4, tap5} <= 6'h0;
            y <= 16'h0;
        end else begin
            tap0 <= x;
            tap1 <= tap0;
            tap2 <= tap1;
            tap3 <= tap2;
            tap4 <= tap3;
            tap5 <= tap4;
            sum <= tap0*(6'd1) + tap1*(6'd2) + tap2*(6'd3) + tap3*(6'd4) + tap4*(6'd5) + tap5*(6'd6);
            y <= sum;
        end
    end

endmodule
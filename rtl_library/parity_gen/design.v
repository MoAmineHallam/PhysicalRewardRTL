// Registered even/odd parity generator for 8-bit data.
// even_par = ^data, odd_par = ~even_par.
module parity_gen (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] data,
    output reg        even_par,
    output reg        odd_par
);
    always @(posedge clk) begin
        if (!rst_n) begin
            even_par <= 1'b0;
            odd_par  <= 1'b1;
        end else begin
            even_par <= ^data;
            odd_par  <= ~(^data);
        end
    end
endmodule

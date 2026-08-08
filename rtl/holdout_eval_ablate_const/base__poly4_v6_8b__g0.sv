module base__poly4_v6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'h0000; // Zero the output
        end else begin
            y <= ((x*x*x*x*65 + x*x*x*29 + x*x*88 + x*44 + 17) % 65536);
        end
    end

endmodule
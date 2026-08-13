module base__poly4_v7_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 0;
        end else begin
            y <= (x * (x * (x * ((x * 24) + 36) + 17) + 21) + 50) & 16'hFFFF;
        end
    end

endmodule
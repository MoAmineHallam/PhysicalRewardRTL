module step2_cnt9b__base__2 (
    input wire clk, rst_n,
    output reg [8:0] count
);

    always @(posedge clk, negedge rst_n) begin
        if (!rst_n) begin
            count <= 9'b0;
        end else begin
            count <= count + 2;
        end
    end

endmodule
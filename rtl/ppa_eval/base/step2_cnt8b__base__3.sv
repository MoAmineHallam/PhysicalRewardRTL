module step2_cnt8b__base__3 (
    input  wire clk, rst_n,
    output reg  [7:0] count
);

    always @(posedge clk, negedge rst_n) begin
        if (~rst_n) begin
            count <= 8'b0;
        end else begin
            count <= count + 2;
        end
    end

endmodule
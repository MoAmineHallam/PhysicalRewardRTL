module step7_cnt12b__base__5 (
    input  wire clk, rst_n,
    output reg  [11:0] count
);

    always @(posedge clk)
    begin
        if (!rst_n) begin
            count <= 0;
        end else begin
            count <= count + 7;
        end
    end

endmodule
module tccnt5_10__base__2 (
    input  wire clk, rst_n,
    output reg  [4:0] count,
    output reg  tc
);

    always @(posedge clk) begin
        if (rst_n == 1'b0) begin
            count <= 0;
            tc <= 0;
        end else begin
            if (count == 5'd10) begin
                count <= 0;
                tc <= 1;
            end else begin
                count <= count + 1;
                tc <= 0;
            end
        end
    end

endmodule
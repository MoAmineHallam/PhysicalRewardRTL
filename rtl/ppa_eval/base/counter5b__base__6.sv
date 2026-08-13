module counter5b__base__6 (
    input  wire clk,
    input  wire rst_n,
    output reg  [4:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (rst_n == 0) begin
            count <= 5'b0;
        end
        else begin
            count <= count + 1;
        end
    end

endmodule
module tccnt4_15__base__0 (
    input  wire clk, rst_n,
    output reg  [3:0] count,
    output reg  tc
);

always @(posedge clk, negedge rst_n) begin
    if (~rst_n) begin
        count <= 4'b0;
        tc <= 1'b0;
    end else begin
        if (count == 4'hf) begin
            count <= 4'b0;
            tc <= 1'b1;
        end else begin
            count <= count + 1;
            tc <= 1'b0;
        end
    end
end

endmodule
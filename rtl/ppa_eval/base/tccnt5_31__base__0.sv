module tccnt5_31__base__0 (
    input  wire clk, rst_n,
    output reg  [4:0] count,
    output reg  tc
);

always @(posedge clk, negedge rst_n) begin
    if (~rst_n) begin
        count <= 0;
        tc <= 0;
    end
    else begin
        if (count == 5'd31) begin
            count <= 0;
            tc <= 1;
        end
        else begin
            count <= count + 1;
            tc <= 0;
        end
    end
end

endmodule
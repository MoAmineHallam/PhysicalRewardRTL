module tccnt5_31__base__5 (
    input  wire clk, rst_n,
    output reg  [4:0] count,
    output reg  tc
);

    always @(posedge clk, negedge rst_n) begin
        if (~rst_n) begin
            count <= 5'b0;
            tc <= 1'b0;
        end
        else begin
            if (count == 5'd31) begin
                tc <= 1'b1;
                count <= 5'b0;
            end
            else begin
                tc <= 1'b0;
                count <= count + 1;
            end
        end
    end

endmodule
// 2-to-1 priority encoder (registered). MSB highest priority.
module prienc2 (
    input  wire clk, rst_n,
    input  wire [1:0] req,
    output reg  [0:0] enc,
    output reg  valid
);
    always @(posedge clk) begin
        if (!rst_n) begin enc<=0; valid<=0; end
        else begin
            valid <= |req;
            if (req[1]) enc <= 1'd1;
            else enc <= 1'd0;
        end
    end
endmodule

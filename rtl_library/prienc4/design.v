// 4-to-2 priority encoder (registered). MSB highest priority.
module prienc4 (
    input  wire clk, rst_n,
    input  wire [3:0] req,
    output reg  [1:0] enc,
    output reg  valid
);
    always @(posedge clk) begin
        if (!rst_n) begin enc<=0; valid<=0; end
        else begin
            valid <= |req;
            if (req[3]) enc <= 2'd3;
            else if (req[2]) enc <= 2'd2;
            else if (req[1]) enc <= 2'd1;
            else enc <= 2'd0;
        end
    end
endmodule

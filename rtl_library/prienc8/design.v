// 8-to-3 priority encoder (registered). MSB highest priority.
module prienc8 (
    input  wire clk, rst_n,
    input  wire [7:0] req,
    output reg  [2:0] enc,
    output reg  valid
);
    always @(posedge clk) begin
        if (!rst_n) begin enc<=0; valid<=0; end
        else begin
            valid <= |req;
            if (req[7]) enc <= 3'd7;
            else if (req[6]) enc <= 3'd6;
            else if (req[5]) enc <= 3'd5;
            else if (req[4]) enc <= 3'd4;
            else if (req[3]) enc <= 3'd3;
            else if (req[2]) enc <= 3'd2;
            else if (req[1]) enc <= 3'd1;
            else enc <= 3'd0;
        end
    end
endmodule

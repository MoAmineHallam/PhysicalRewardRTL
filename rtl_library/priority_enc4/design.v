// Registered 4-to-2 priority encoder. req[3] has highest priority.
module priority_enc4 (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [3:0] req,
    output reg  [1:0] enc,
    output reg        valid
);
    always @(posedge clk) begin
        if (!rst_n) begin
            enc   <= 2'b0;
            valid <= 1'b0;
        end else begin
            valid <= |req;
            if      (req[3]) enc <= 2'd3;
            else if (req[2]) enc <= 2'd2;
            else if (req[1]) enc <= 2'd1;
            else             enc <= 2'd0;
        end
    end
endmodule

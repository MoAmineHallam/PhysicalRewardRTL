// Golden reference: priority encoder with registered output
// Finds index of highest set bit; valid=0 when in==0
module comb_always (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] in,
    output reg  [2:0] out,
    output reg        valid
);
    reg [2:0] enc;
    reg       vld;

    always @(*) begin
        enc = 3'd0; vld = 1'b0;
        if      (in[7]) begin enc = 3'd7; vld = 1'b1; end
        else if (in[6]) begin enc = 3'd6; vld = 1'b1; end
        else if (in[5]) begin enc = 3'd5; vld = 1'b1; end
        else if (in[4]) begin enc = 3'd4; vld = 1'b1; end
        else if (in[3]) begin enc = 3'd3; vld = 1'b1; end
        else if (in[2]) begin enc = 3'd2; vld = 1'b1; end
        else if (in[1]) begin enc = 3'd1; vld = 1'b1; end
        else if (in[0]) begin enc = 3'd0; vld = 1'b1; end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            out   <= 3'b0;
            valid <= 1'b0;
        end else begin
            out   <= enc;
            valid <= vld;
        end
    end
endmodule

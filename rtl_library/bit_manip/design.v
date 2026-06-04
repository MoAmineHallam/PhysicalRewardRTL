// Golden reference: bit-reversal and popcount, registered outputs
module bit_manip (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] in,
    output reg  [7:0] reversed,
    output reg  [3:0] popcount
);
    integer i;
    reg [7:0] rev;
    reg [3:0] cnt;

    always @(*) begin
        for (i = 0; i < 8; i = i + 1)
            rev[i] = in[7-i];
        cnt = in[0]+in[1]+in[2]+in[3]+in[4]+in[5]+in[6]+in[7];
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            reversed <= 8'b0;
            popcount <= 4'b0;
        end else begin
            reversed <= rev;
            popcount <= cnt;
        end
    end
endmodule

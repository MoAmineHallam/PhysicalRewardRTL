module base__fir6_8b__g8 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] past_sample_0;
reg [7:0] past_sample_1;
reg [7:0] past_sample_2;
reg [7:0] past_sample_3;
reg [7:0] past_sample_4;
reg [7:0] past_sample_5;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        past_sample_0 <= 0;
        past_sample_1 <= 0;
        past_sample_2 <= 0;
        past_sample_3 <= 0;
        past_sample_4 <= 0;
        past_sample_5 <= 0;
        y <= 0;
    end else begin
        // shift in the new sample
        past_sample_0 <= x;
        past_sample_1 <= past_sample_0;
        past_sample_2 <= past_sample_1;
        past_sample_3 <= past_sample_2;
        past_sample_4 <= past_sample_3;
        past_sample_5 <= past_sample_4;

        // calculate the new output
        y <= (past_sample_0 * 3) + (past_sample_1 * 5) + (past_sample_2 * 7) + (past_sample_3 * 7) + (past_sample_4 * 5) + (past_sample_5 * 3);
    end
end

endmodule
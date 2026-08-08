module base__firr26__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap [25:0];
    integer k;
    reg [15:0] sum = 0;

    always @(posedge clk, negedge rst_n) begin
        if (~rst_n) begin
            for (k = 0; k < 26; k = k + 1) begin
                tap[k] <= 0;
            end
            sum <= 0;
            y <= 0;
        end
        else begin
            for (k = 25; k > 0; k = k - 1) begin
                tap[k] <= tap[k-1];
            end
            tap[0] <= x;
            sum <= 0;
            for (k = 0; k < 26; k = k + 1) begin
                sum = sum + (k+1)*tap[k];
            end
            y <= sum[15:0];
        end
    end

endmodule
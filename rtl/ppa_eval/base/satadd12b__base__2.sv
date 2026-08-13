module satadd12b__base__2 (
    input  wire clk, rst_n,
    input  wire [11:0] a,
    input  wire [11:0] b,
    output reg  [11:0] sum
);

    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) begin
            sum <= 12'b0;
        end
        else begin
            if ((a + b) > 12'hFFF) begin
                sum <= 12'hFFF;
            end
            else begin
                sum <= a + b;
            end
        end
    end

endmodule
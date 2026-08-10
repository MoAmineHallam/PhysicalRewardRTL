module base__firr40__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [39:0];
    reg [15:0] temp_sum;
    integer k;

    always @(posedge clk) begin
        if (!rst_n) begin
            for (k = 0; k < 40; k = k + 1) begin
                delay_line[k] <= 0;
            end
            y <= 0;
        end else begin
            delay_line[0] <= x;
            temp_sum = 0;
            for (k = 0; k < 40; k = k + 1) begin
                temp_sum = temp_sum + ((k+1)*delay_line[k]);
            end
            y <= temp_sum[15:0];
            for (k = 39; k > 0; k = k - 1) begin
                delay_line[k] <= delay_line[k-1];
            end
        end
    end

endmodule
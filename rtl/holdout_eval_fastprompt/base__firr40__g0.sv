module base__firr40__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap [39:0];
    wire [15:0] sum[39:1];
    integer i;

    // Initialize the tap values to 0
    initial begin
        for (i = 0; i < 40; i = i + 1) begin
            tap[i] = 8'h00;
        end
    end

    // Shift in the new sample on each cycle
    always @(posedge clk, negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 40; i = i + 1) begin
                tap[i] <= 8'h00;
            end
        end
        else begin
            for (i = 39; i > 0; i = i - 1) begin
                tap[i] <= tap[i-1];
            end
            tap[0] <= x;
        end
    end

    // Compute the sum for each k
    genvar k;
    generate
        for (k = 1; k < 40; k = k + 1) begin
            assign sum[k] = (k+1) * tap[k];
        end
    endgenerate

    // Compute the output on each cycle
    always @(posedge clk, negedge rst_n) begin
        if (!rst_n) begin
            y <= 16'h0000;
        end
        else begin
            y <= sum[39] + sum[38] + sum[37] + sum[36] + sum[35] + sum[34] + sum[33] + sum[32] +
                 sum[31] + sum[30] + sum[29] + sum[28] + sum[27] + sum[26] + sum[25] + sum[24] +
                 sum[23] + sum[22] + sum[21] + sum[20] + sum[19] + sum[18] + sum[17] + sum[16] +
                 sum[15] + sum[14] + sum[13] + sum[12] + sum[11] + sum[10] + sum[9] + sum[8] + sum[7] + sum[6] + sum[5] + sum[4] + sum[3] + sum[2] + sum[1] + tap[0];
        end
    end

endmodule
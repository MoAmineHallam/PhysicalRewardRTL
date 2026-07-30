module base__firr18__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] tap [17:0]; // 18 element delay line
integer   i;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // Reset the delay line and output
        for (i = 0; i < 18; i = i + 1) begin
            tap[i] <= 0;
        end
        y <= 0;
    end else begin
        // Shift the delay line and update the newest tap
        for (i = 17; i > 0; i = i - 1) begin
            tap[i] <= tap[i-1];
        end
        tap[0] <= x;
        // Calculate the output
        y <= {12'b0, $signed($signed({3'b0, tap[0]}) * 1)} +
             {12'b0, $signed($signed({3'b0, tap[1]}) * 2)} +
             {12'b0, $signed($signed({3'b0, tap[2]}) * 3)} +
             {12'b0, $signed($signed({3'b0, tap[3]}) * 4)} +
             {12'b0, $signed($signed({3'b0, tap[4]}) * 5)} +
             {12'b0, $signed($signed({3'b0, tap[5]}) * 6)} +
             {12'b0, $signed($signed({3'b0, tap[6]}) * 7)} +
             {12'b0, $signed($signed({3'b0, tap[7]}) * 8)} +
             {12'b0, $signed($signed({3'b0, tap[8]}) * 9)} +
             {12'b0, $signed($signed({3'b0, tap[9]}) * 10)} +
             {12'b0, $signed($signed({3'b0, tap[10]}) * 11)} +
             {12'b0, $signed($signed({3'b0, tap[11]}) * 12)} +
             {12'b0, $signed($signed({3'b0, tap[12]}) * 13)} +
             {12'b0, $signed($signed({3'b0, tap[13]}) * 14)} +
             {12'b0, $signed($signed({3'b0, tap[14]}) * 15)} +
             {12'b0, $signed($signed({3'b0, tap[15]}) * 16)} +
             {12'b0, $signed($signed({3'b0, tap[16]}) * 17)} +
             {12'b0, $signed($signed({3'b0, tap[17]}) * 18)};
    end
end

endmodule
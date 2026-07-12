module base__firr6__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap [0:5];
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 6; i = i + 1) begin
                tap[i] <= 8'b0;
            end
            y <= 16'b0;
        end else begin
            // push x into the shift register
            for (i = 4; i >= 0; i = i - 1) begin
                tap[i+1] <= tap[i];
            end
            tap[0] <= x;
            
            // calculate the sum over k=0..5 of (k+1)*tap[k]
            y <= ( tap[0] + 2*tap[1] + 3*tap[2] + 4*tap[3] + 5*tap[4] + 6*tap[5] );
        end
    end

endmodule
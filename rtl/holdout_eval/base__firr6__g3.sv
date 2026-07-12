module base__firr6__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] tap [0:5];

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // clear delay line and output
        for (int i=0; i<6; i=i+1) begin
            tap[i] <= 8'h00;
        end
        y <= 16'h0000;
    end
    else begin
        // shift delay line and add new sample
        for (int i=5; i>0; i=i-1) begin
            tap[i] <= tap[i-1];
        end
        tap[0] <= x;

        // compute output
        y <= {12'h0, tap[0]} * 1 + {8'h00, tap[1]} * 2 + {8'h00, tap[2]} * 3 + {8'h00, tap[3]} * 4 + {8'h00, tap[4]} * 5 + {8'h00, tap[5]} * 6;
    end
end

endmodule
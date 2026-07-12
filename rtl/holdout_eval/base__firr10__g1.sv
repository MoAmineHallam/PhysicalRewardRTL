module base__firr10__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] tap [0:9];
integer i;

always @(posedge clk) begin
    if (!rst_n) begin
        for (i = 0; i < 10; i = i + 1) begin
            tap[i] <= 0;
        end
        y <= 0;
    end else begin
        for (i = 9; i > 0; i = i - 1) begin
            tap[i] <= tap[i-1];
        end
        tap[0] <= x;
        y <= {8'b0, 8'b0} + {8'b0, tap[0]}*1 + {8'b0, tap[1]}*2 + {8'b0, tap[2]}*3 + {8'b0, tap[3]}*4 + {8'b0, tap[4]}*5 + {8'b0, tap[5]}*6 + {8'b0, tap[6]}*7 + {8'b0, tap[7]}*8 + {8'b0, tap[8]}*9 + {8'b0, tap[9]}*10;
    end
end

endmodule
module base__firr10__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap0, tap1, tap2, tap3, tap4, tap5, tap6, tap7, tap8, tap9;

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
            tap0 <= 0;
            tap1 <= 0;
            tap2 <= 0;
            tap3 <= 0;
            tap4 <= 0;
            tap5 <= 0;
            tap6 <= 0;
            tap7 <= 0;
            tap8 <= 0;
            tap9 <= 0;
        end else begin
            tap0 <= x;
            tap1 <= tap0;
            tap2 <= tap1;
            tap3 <= tap2;
            tap4 <= tap3;
            tap5 <= tap4;
            tap6 <= tap5;
            tap7 <= tap6;
            tap8 <= tap7;
            tap9 <= tap8;
            y <= {1'b0, tap0}*(1) + {1'b0, tap1}*(2) + {1'b0, tap2}*(3) + {1'b0, tap3}*(4) + {1'b0, tap4}*(5) + {1'b0, tap5}*(6) + {1'b0, tap6}*(7) + {1'b0, tap7}*(8) + {1'b0, tap8}*(9) + {1'b0, tap9}*(10);
        end
    end
endmodule
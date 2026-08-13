module base__fir18_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] delay_line [17:0];
    integer i;

    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 18; i = i + 1) begin
                delay_line[i] <= 8'd0;
            end
            y <= 16'd0;
        end else begin
            delay_line[0] <= x;
            for (i = 1; i < 18; i = i + 1) begin
                delay_line[i] <= delay_line[i-1];
            end
            y <= {8'd0, x} * 3 + {8'd0, delay_line[0]} * 5 + {8'd0, delay_line[1]} * 7 + {8'd0, delay_line[2]} * 9 + {8'd0, delay_line[3]} * 11 + {8'd0, delay_line[4]} * 13 + {8'd0, delay_line[5]} * 15 + {8'd0, delay_line[6]} * 17 + {8'd0, delay_line[7]} * 19 + {8'd0, delay_line[8]} * 19 + {8'd0, delay_line[9]} * 17 + {8'd0, delay_line[10]} * 15 + {8'd0, delay_line[11]} * 13 + {8'd0, delay_line[12]} * 11 + {8'd0, delay_line[13]} * 9 + {8'd0, delay_line[14]} * 7 + {8'd0, delay_line[15]} * 5 + {8'd0, delay_line[16]} * 3;
        end
    end

endmodule
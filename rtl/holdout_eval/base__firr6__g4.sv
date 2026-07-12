module base__firr6__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap [0:5];
    integer k;
    
    always @(posedge clk) begin
        if (!rst_n) begin
            for (k=0; k<6; k=k+1) begin
                tap[k] <= 8'b0;
            end
            y <= 16'b0;
        end
        else begin
            // Shift the old samples to make room for the new one
            for (k=5; k>0; k=k-1) begin
                tap[k] <= tap[k-1];
            end
            // Add the new sample to the end
            tap[0] <= x;
            // Compute the output from the low 16 bits of the sum over k=0..5 of (k+1)*tap[k]
            y <= {12'b0, 4'b0} + {5'b0, tap[0]}*6'd1 + {5'b0, tap[1]}*6'd2 + {5'b0, tap[2]}*6'd3 + {5'b0, tap[3]}*6'd4 + {5'b0, tap[4]}*6'd5 + {5'b0, tap[5]}*6'd6;
        end
    end
    
endmodule
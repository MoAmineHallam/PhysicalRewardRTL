module counter6b__v4_s100__6 (
    input  wire clk,
    input  wire rst_n,
    output reg  [5:0] count
);

    always @(posedge clk or negedge rst_n)
    begin
        if (~rst_n) // active-low reset
            count <= 6'b0;
        else
            count <= count + 1;
    end

endmodule
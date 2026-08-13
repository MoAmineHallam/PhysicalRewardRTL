module mod2_counter__v4_s100__1 (
    input  wire clk,
    input  wire rst_n,
    output reg  [0:0] count
);

    reg [1:0] state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= 2'b00;
            count <= 1'b0;
        end
        else begin
            state <= state + 1;
            count <= state[0];
        end
    end

endmodule
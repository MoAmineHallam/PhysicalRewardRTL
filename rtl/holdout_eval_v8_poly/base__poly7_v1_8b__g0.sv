module base__poly7_v1_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 0;
        end else begin
            y <= ((x*(x*(x*(x*(x*(x*(x*16+91)+42)+85)+48)+89)+88)+18)%(1<<16));
        end
    end

endmodule
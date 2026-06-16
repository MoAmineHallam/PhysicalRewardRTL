module mod21_counter__c4 (
    input  wire clk,
    input  wire rst_n,
    output reg  [4:0] count
);
    always @(posedge clk, negedge rst_n) begin
        if (!rst_n) begin
            count <= 5'b0;
        end else begin
            if (count == 5'd20) begin
                count <= 5'b0;
            end else begin
                count <= count + 1;
            end
        end
    end
endmodule
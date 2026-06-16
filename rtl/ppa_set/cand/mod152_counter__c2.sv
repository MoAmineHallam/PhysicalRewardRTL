module mod152_counter__c2 (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        count <= 0;
    end else if (count == 151) begin
        count <= 0;
    end else begin
        count <= count + 1;
    end
end

endmodule
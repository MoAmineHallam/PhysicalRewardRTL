`timescale 1ns/1ps
// Logic Analyzer with software-start and rising-edge trigger modes.
// Register map (byte addresses, word-aligned):
//   0x00 CTRL   : bit0=arm/start, bit1=trigger_mode (0=sw-start, 1=edge-trigger)
//                 bits[4:2]=sel (selects active DUT 0-6, set alongside arm or alone)
//   0x04 STATUS : bit0=done, bit1=armed (waiting for trigger)
//   0x08 RADDR  : buffer read index
//   0x0C RDATA  : buffer[RADDR]
module la_axi #(
    parameter DW    = 16,
    parameter DEPTH = 32768,
    parameter AW    = 15
)(
    input  wire        S_AXI_ACLK,
    input  wire        S_AXI_ARESETN,
    input  wire [3:0]  S_AXI_AWADDR,
    input  wire        S_AXI_AWVALID,
    output reg         S_AXI_AWREADY,
    input  wire [31:0] S_AXI_WDATA,
    input  wire [3:0]  S_AXI_WSTRB,
    input  wire        S_AXI_WVALID,
    output reg         S_AXI_WREADY,
    output reg  [1:0]  S_AXI_BRESP,
    output reg         S_AXI_BVALID,
    input  wire        S_AXI_BREADY,
    input  wire [3:0]  S_AXI_ARADDR,
    input  wire        S_AXI_ARVALID,
    output reg         S_AXI_ARREADY,
    output reg  [31:0] S_AXI_RDATA,
    output reg  [1:0]  S_AXI_RRESP,
    output reg         S_AXI_RVALID,
    input  wire        S_AXI_RREADY,
    input  wire [DW-1:0] probe,
    output wire [2:0]  sel
);
    // FSM states
    localparam IDLE      = 2'd0;
    localparam ARMED     = 2'd1;
    localparam CAPTURING = 2'd2;
    localparam DONE      = 2'd3;

    reg [DW-1:0] buffer [0:DEPTH-1];
    reg [AW-1:0] wr_addr;
    reg [1:0]    state;
    reg          done;
    reg          arm_pulse;
    reg          trig_mode;
    reg [2:0]    sel_reg;

    assign sel = sel_reg;

    // edge detection on probe[0]
    reg probe0_prev;
    wire rising_edge = probe[0] & ~probe0_prev;

    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) begin
            state       <= IDLE;
            wr_addr     <= {AW{1'b0}};
            done        <= 1'b0;
            probe0_prev <= 1'b0;
        end else begin
            probe0_prev <= probe[0];
            case (state)
                IDLE: begin
                    if (arm_pulse) begin
                        done    <= 1'b0;
                        wr_addr <= {AW{1'b0}};
                        if (trig_mode)
                            state <= ARMED;
                        else
                            state <= CAPTURING;
                    end
                end
                ARMED: begin
                    if (rising_edge)
                        state <= CAPTURING;
                end
                CAPTURING: begin
                    buffer[wr_addr] <= probe;
                    if (wr_addr == DEPTH-1) begin
                        state <= DONE;
                        done  <= 1'b1;
                    end else begin
                        wr_addr <= wr_addr + 1'b1;
                    end
                end
                DONE: ;
            endcase
        end
    end

    // AXI register file
    reg [AW-1:0] rd_index;
    wire [DW-1:0] buf_q = buffer[rd_index];
    wire wr_ok = S_AXI_AWVALID && S_AXI_WVALID && !S_AXI_BVALID;

    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) begin
            S_AXI_AWREADY <= 1'b0;
            S_AXI_WREADY  <= 1'b0;
            S_AXI_BVALID  <= 1'b0;
            S_AXI_BRESP   <= 2'b00;
            rd_index      <= {AW{1'b0}};
            arm_pulse     <= 1'b0;
            trig_mode     <= 1'b0;
            sel_reg       <= 3'b0;
        end else begin
            arm_pulse <= 1'b0;
            if (wr_ok) begin
                S_AXI_AWREADY <= 1'b1;
                S_AXI_WREADY  <= 1'b1;
                case (S_AXI_AWADDR[3:2])
                    2'd0: begin
                        if (S_AXI_WDATA[0]) arm_pulse <= 1'b1;
                        trig_mode <= S_AXI_WDATA[1];
                        sel_reg   <= S_AXI_WDATA[4:2];
                    end
                    2'd2: rd_index <= S_AXI_WDATA[AW-1:0];
                    default: ;
                endcase
                S_AXI_BVALID <= 1'b1;
                S_AXI_BRESP  <= 2'b00;
            end else begin
                S_AXI_AWREADY <= 1'b0;
                S_AXI_WREADY  <= 1'b0;
                if (S_AXI_BVALID && S_AXI_BREADY)
                    S_AXI_BVALID <= 1'b0;
            end
        end
    end

    always @(posedge S_AXI_ACLK) begin
        if (!S_AXI_ARESETN) begin
            S_AXI_ARREADY <= 1'b0;
            S_AXI_RVALID  <= 1'b0;
            S_AXI_RRESP   <= 2'b00;
            S_AXI_RDATA   <= 32'd0;
        end else begin
            if (S_AXI_ARVALID && !S_AXI_RVALID) begin
                S_AXI_ARREADY <= 1'b1;
                case (S_AXI_ARADDR[3:2])
                    2'd1: S_AXI_RDATA <= {30'd0, (state == ARMED), done};
                    2'd3: S_AXI_RDATA <= {{(32-DW){1'b0}}, buf_q};
                    default: S_AXI_RDATA <= 32'd0;
                endcase
                S_AXI_RVALID <= 1'b1;
                S_AXI_RRESP  <= 2'b00;
            end else begin
                S_AXI_ARREADY <= 1'b0;
                if (S_AXI_RVALID && S_AXI_RREADY)
                    S_AXI_RVALID <= 1'b0;
            end
        end
    end
endmodule

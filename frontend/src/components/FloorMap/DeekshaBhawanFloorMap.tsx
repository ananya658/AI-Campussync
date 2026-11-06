import React from 'react';
import { Room } from '../../types';

interface DeekshaBhawanFloorMapProps {
  floorNumber: number; // 0 (Ground), 1 (First)
  rooms: Room[];
  selectedRoomId?: number;
  onSelectRoom: (room: Room) => void;
}

export const DeekshaBhawanFloorMap: React.FC<DeekshaBhawanFloorMapProps> = ({
  floorNumber,
  rooms,
  selectedRoomId,
  onSelectRoom
}) => {
  const getRoomColor = (room?: Room, isSelected?: boolean) => {
    if (isSelected) return { fill: '#2563EB', stroke: '#1D4ED8', text: '#FFFFFF', badgeBg: '#1D4ED8' };
    if (!room) return { fill: '#F1F5F9', stroke: '#CBD5E1', text: '#64748B', badgeBg: '#E2E8F0' };

    // LH13 / LH14 Discrepancy Flag
    if (room.verification_status === 'PENDING_ADMIN_VERIFICATION') {
      return { fill: '#FEF3C7', stroke: '#D97706', text: '#92400E', badgeBg: '#FDE68A' };
    }

    if (!room.is_active || room.is_maintenance) {
      return { fill: '#E2E8F0', stroke: '#94A3B8', text: '#475569', badgeBg: '#CBD5E1' };
    }

    switch (room.current_status) {
      case 'BOOKED':
        return { fill: '#FEE2E2', stroke: '#EF4444', text: '#991B1B', badgeBg: '#FCA5A5' };
      case 'PENDING_APPROVAL':
        return { fill: '#FEF3C7', stroke: '#F59E0B', text: '#92400E', badgeBg: '#FCD34D' };
      case 'AVAILABLE':
      default:
        return { fill: '#D1FAE5', stroke: '#10B981', text: '#065F46', badgeBg: '#6EE7B7' };
    }
  };

  const findRoom = (roomNumber: string) => {
    return rooms.find(
      (r) => r.room_number.toLowerCase().replace(/[^a-z0-9]/g, '') === roomNumber.toLowerCase().replace(/[^a-z0-9]/g, '')
    );
  };

  const renderLectureHall = (
    roomNumber: string,
    x: number,
    y: number,
    width: number,
    height: number,
    isDiscrepancy: boolean = false
  ) => {
    const room = findRoom(roomNumber);
    const isSelected = room && room.id === selectedRoomId;
    const colors = getRoomColor(room, isSelected);

    return (
      <g
        key={roomNumber}
        onClick={() => room && onSelectRoom(room)}
        className="cursor-pointer group transition-all duration-200"
      >
        {isSelected && (
          <rect
            x={x - 3}
            y={y - 3}
            width={width + 6}
            height={height + 6}
            rx={8}
            fill="none"
            stroke="#3B82F6"
            strokeWidth={3}
            strokeDasharray="4 2"
            className="animate-pulse"
          />
        )}

        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          rx={6}
          fill={isDiscrepancy && !isSelected ? 'url(#discrepancy-hatch)' : colors.fill}
          stroke={colors.stroke}
          strokeWidth={isSelected ? 2.5 : (isDiscrepancy ? 2 : 1.5)}
          className="group-hover:opacity-90 group-hover:stroke-blue-500 transition-all drop-shadow-sm"
        />

        {/* Status Indicator */}
        <circle
          cx={x + width - 14}
          cy={y + 14}
          r={4}
          fill={colors.stroke}
          className={room?.current_status === 'AVAILABLE' ? 'animate-pulse' : ''}
        />

        {/* Room Header */}
        <text
          x={x + 12}
          y={y + 24}
          fontSize={13}
          fontWeight="bold"
          fill={colors.text}
          className="select-none font-sans"
        >
          {roomNumber}
        </text>

        {/* Subtitle / Discrepancy label */}
        <text
          x={x + 12}
          y={y + 40}
          fontSize={9.5}
          fill={isSelected ? '#DBEAFE' : colors.text}
          opacity={0.85}
          className="select-none font-sans"
        >
          {isDiscrepancy ? '⚠ Blueprint Discrepancy' : 'Lecture Hall (Cap 90)'}
        </text>

        {/* Tiered Lecture Seating Curves inside SVG for realistic architectural look */}
        <path
          d={`M ${x + 15} ${y + 60} Q ${x + width / 2} ${y + 55} ${x + width - 15} ${y + 60}`}
          fill="none"
          stroke={isSelected ? '#60A5FA' : colors.stroke}
          strokeWidth={1}
          opacity={0.4}
        />
        <path
          d={`M ${x + 15} ${y + 75} Q ${x + width / 2} ${y + 70} ${x + width - 15} ${y + 75}`}
          fill="none"
          stroke={isSelected ? '#60A5FA' : colors.stroke}
          strokeWidth={1}
          opacity={0.4}
        />

        {/* Capacity badge */}
        {room && (
          <g transform={`translate(${x + 12}, ${y + height - 24})`}>
            <rect
              x={0}
              y={0}
              width={isDiscrepancy ? 74 : 54}
              height={16}
              rx={4}
              fill={colors.badgeBg}
              opacity={0.8}
            />
            <text
              x={isDiscrepancy ? 37 : 27}
              y={12}
              fontSize={8.5}
              fontWeight="bold"
              fill={colors.text}
              textAnchor="middle"
              className="select-none font-sans"
            >
              {isDiscrepancy ? 'Unverified' : `Cap: ${room.capacity}`}
            </text>
          </g>
        )}
      </g>
    );
  };

  return (
    <div className="relative w-full bg-slate-900/5 rounded-2xl p-4 md:p-6 border border-slate-200/80 overflow-x-auto">
      <svg
        viewBox="0 0 960 520"
        className="w-full h-auto min-w-[750px] max-w-full drop-shadow-sm"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern id="db-grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#F1F5F9" strokeWidth="0.8" />
          </pattern>
          {/* Hatched pattern for LH13 and LH14 discrepancy */}
          <pattern id="discrepancy-hatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="8" stroke="#FDE68A" strokeWidth="3" />
            <line x1="0" y1="0" x2="8" y2="0" stroke="#FEF3C7" strokeWidth="5" />
          </pattern>
        </defs>

        <rect width="960" height="520" fill="#FFFFFF" rx="16" stroke="#E2E8F0" strokeWidth="2" />
        <rect width="960" height="520" fill="url(#db-grid)" rx="16" />

        {/* Exterior Boundary */}
        <rect
          x="30"
          y="30"
          width="900"
          height="460"
          rx="12"
          fill="none"
          stroke="#0F172A"
          strokeWidth="3.5"
        />

        {/* Central Entrance */}
        <path d="M 440 490 L 520 490 L 510 480 L 450 480 Z" fill="#E2E8F0" stroke="#64748B" />
        <text x="480" y="506" fill="#475569" fontSize="10" fontWeight="bold" textAnchor="middle">
          DEEKSHA BHAWAN ENTRANCE (100M FROM IET)
        </text>

        {/* ================= FLOOR 0: GROUND FLOOR (LH01 - LH07) ================= */}
        {floorNumber === 0 && (
          <g id="db-ground-floor">
            {/* Grand central gallery corridor */}
            <rect x="50" y="235" width="860" height="60" fill="#F8FAFC" stroke="#CBD5E1" strokeDasharray="3 3" />
            <text x="480" y="270" fill="#94A3B8" fontSize="12" fontWeight="600" textAnchor="middle" letterSpacing="3">
              CENTRAL CORRIDOR • GROUND LEVEL (LH01 - LH07)
            </text>

            {/* North Row: LH01, LH02, LH03, LH04 */}
            {renderLectureHall('LH01', 50, 50, 205, 165)}
            {renderLectureHall('LH02', 270, 50, 205, 165)}
            {renderLectureHall('LH03', 490, 50, 205, 165)}
            {renderLectureHall('LH04', 710, 50, 200, 165)}

            {/* South Row: LH05, LH06, LH07 */}
            {renderLectureHall('LH05', 50, 315, 275, 155)}
            {renderLectureHall('LH06', 345, 315, 275, 155)}
            {renderLectureHall('LH07', 640, 315, 270, 155)}
          </g>
        )}

        {/* ================= FLOOR 1: FIRST FLOOR (LH08 - LH14) ================= */}
        {floorNumber === 1 && (
          <g id="db-first-floor">
            <rect x="50" y="235" width="860" height="60" fill="#F8FAFC" stroke="#CBD5E1" strokeDasharray="3 3" />
            <text x="480" y="270" fill="#94A3B8" fontSize="12" fontWeight="600" textAnchor="middle" letterSpacing="3">
              FIRST FLOOR CONCOURSE • OFFICIAL (LH08-LH12) & DISCREPANCY (LH13, LH14)
            </text>

            {/* North Row: LH08, LH09, LH10, LH11 */}
            {renderLectureHall('LH08', 50, 50, 205, 165)}
            {renderLectureHall('LH09', 270, 50, 205, 165)}
            {renderLectureHall('LH10', 490, 50, 205, 165)}
            {renderLectureHall('LH11', 710, 50, 200, 165)}

            {/* South Row: LH12 (official), LH13 (discrepancy), LH14 (discrepancy) */}
            {renderLectureHall('LH12', 50, 315, 275, 155)}
            {renderLectureHall('LH13', 345, 315, 275, 155, true)}
            {renderLectureHall('LH14', 640, 315, 270, 155, true)}
          </g>
        )}

        {/* Legend with Discrepancy notice */}
        <g transform="translate(40, 498)">
          <circle cx="10" cy="5" r="4" fill="#10B981" />
          <text x="20" y="9" fontSize="10" fill="#475569" fontWeight="500">Available</text>

          <circle cx="95" cy="5" r="4" fill="#EF4444" />
          <text x="105" y="9" fontSize="10" fill="#475569" fontWeight="500">Booked</text>

          <circle cx="165" cy="5" r="4" fill="#2563EB" />
          <text x="175" y="9" fontSize="10" fill="#475569" fontWeight="500">Selected</text>

          <circle cx="245" cy="5" r="4" fill="#D97706" />
          <text x="255" y="9" fontSize="10" fill="#92400E" fontWeight="600">LH13/LH14 Discrepancy (Pending Verification)</text>
        </g>
      </svg>
    </div>
  );
};

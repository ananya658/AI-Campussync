import React from 'react';
import { Room } from '../../types';

interface IETFloorMapProps {
  floorNumber: number; // 0, 1, 2
  rooms: Room[];
  selectedRoomId?: number;
  onSelectRoom: (room: Room) => void;
}

export const IETFloorMap: React.FC<IETFloorMapProps> = ({
  floorNumber,
  rooms,
  selectedRoomId,
  onSelectRoom
}) => {
  const getRoomColor = (room?: Room, isSelected?: boolean) => {
    if (isSelected) return { fill: '#2563EB', stroke: '#1D4ED8', text: '#FFFFFF', badgeBg: '#1D4ED8' }; // Selected (Blue)
    if (!room) return { fill: '#F1F5F9', stroke: '#CBD5E1', text: '#64748B', badgeBg: '#E2E8F0' };

    if (!room.is_active || room.is_maintenance) {
      return { fill: '#E2E8F0', stroke: '#94A3B8', text: '#475569', badgeBg: '#CBD5E1' }; // Maintenance (Grey)
    }

    switch (room.current_status) {
      case 'BOOKED':
        return { fill: '#FEE2E2', stroke: '#EF4444', text: '#991B1B', badgeBg: '#FCA5A5' }; // Booked (Red)
      case 'PENDING_APPROVAL':
        return { fill: '#FEF3C7', stroke: '#F59E0B', text: '#92400E', badgeBg: '#FCD34D' }; // Pending (Yellow)
      case 'AVAILABLE':
      default:
        return { fill: '#D1FAE5', stroke: '#10B981', text: '#065F46', badgeBg: '#6EE7B7' }; // Available (Green)
    }
  };

  const findRoom = (roomNumber: string) => {
    return rooms.find(
      (r) => r.room_number.toLowerCase().replace(/[^a-z0-9]/g, '') === roomNumber.toLowerCase().replace(/[^a-z0-9]/g, '')
    );
  };

  const renderRoomRect = (
    roomNumber: string,
    x: number,
    y: number,
    width: number,
    height: number,
    customLabel?: string,
    subLabel?: string
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
        {/* Shadow for selected */}
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

        {/* Room Box */}
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          rx={6}
          fill={colors.fill}
          stroke={colors.stroke}
          strokeWidth={isSelected ? 2.5 : 1.5}
          className="group-hover:opacity-90 group-hover:stroke-blue-500 transition-all drop-shadow-sm"
        />

        {/* Status Dot */}
        <circle
          cx={x + width - 14}
          cy={y + 14}
          r={4}
          fill={colors.stroke}
          className={room?.current_status === 'AVAILABLE' ? 'animate-pulse' : ''}
        />

        {/* Room Title */}
        <text
          x={x + 12}
          y={y + 24}
          fontSize={13}
          fontWeight="bold"
          fill={colors.text}
          className="select-none font-sans"
        >
          {customLabel || room?.room_number || roomNumber}
        </text>

        {/* Subtitle / Description */}
        <text
          x={x + 12}
          y={y + 40}
          fontSize={10}
          fill={isSelected ? '#DBEAFE' : colors.text}
          opacity={0.85}
          className="select-none font-sans"
        >
          {subLabel || room?.room_name || ''}
        </text>

        {/* Capacity pill */}
        {room && (
          <g transform={`translate(${x + 12}, ${y + height - 24})`}>
            <rect
              x={0}
              y={0}
              width={54}
              height={16}
              rx={4}
              fill={colors.badgeBg}
              opacity={0.6}
            />
            <text
              x={27}
              y={12}
              fontSize={9}
              fontWeight="bold"
              fill={colors.text}
              textAnchor="middle"
              className="select-none font-sans"
            >
              Cap: {room.capacity}
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
        {/* Background Canvas */}
        <rect width="960" height="520" fill="#FFFFFF" rx="16" stroke="#E2E8F0" strokeWidth="2" />

        {/* Grid pattern */}
        <defs>
          <pattern id="iet-grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#F1F5F9" strokeWidth="0.8" />
          </pattern>
        </defs>
        <rect width="960" height="520" fill="url(#iet-grid)" rx="16" />

        {/* Building Exterior Boundary Wall */}
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

        {/* ================= FLOOR 0: GROUND FLOOR ================= */}
        {floorNumber === 0 && (
          <g id="iet-ground-floor">
            {/* Main Central Corridor Circulation Area */}
            <rect x="50" y="240" width="860" height="70" fill="#F8FAFC" stroke="#CBD5E1" strokeDasharray="3 3" />
            <text x="480" y="280" fill="#94A3B8" fontSize="12" fontWeight="600" textAnchor="middle" letterSpacing="3">
              CENTRAL GROUND CORRIDOR & FOYER
            </text>

            {/* Entrance Porch */}
            <path d="M 440 500 L 520 500 L 510 490 L 450 490 Z" fill="#E2E8F0" stroke="#64748B" />
            <text x="480" y="508" fill="#475569" fontSize="10" fontWeight="bold" textAnchor="middle">
              MAIN CAMPUS ENTRANCE
            </text>

            {/* North Wing: Central Engineering Library (150-180 students) */}
            {renderRoomRect('Library', 50, 50, 420, 170, 'CENTRAL LIBRARY', 'Academic Reading & Reference Hall (Cap 180)')}

            {/* Placement Cell */}
            {renderRoomRect('Placement-Cell', 490, 50, 420, 80, 'T&P PLACEMENT CELL', 'Training & Corporate Recruitment Cell')}

            {/* Teachers Office Lounge */}
            {renderRoomRect('Teachers-Office', 490, 140, 420, 80, "TEACHERS' OFFICE", 'Faculty Central Workspace & Cabin Lounge')}

            {/* South Wing: Administrative Office & Directorate */}
            {renderRoomRect('Admin-Office', 50, 330, 420, 140, 'ADMINISTRATIVE OFFICE', 'Academic Registrar & Student Affairs')}

            {renderRoomRect('Directors-Office', 490, 330, 420, 140, "DIRECTOR'S OFFICE", 'Executive Boardroom & Director Directorate')}
          </g>
        )}

        {/* ================= FLOOR 1: FIRST FLOOR ================= */}
        {floorNumber === 1 && (
          <g id="iet-first-floor">
            {/* First Floor Corridor */}
            <rect x="50" y="235" width="860" height="60" fill="#F8FAFC" stroke="#CBD5E1" strokeDasharray="3 3" />
            <text x="480" y="270" fill="#94A3B8" fontSize="12" fontWeight="600" textAnchor="middle" letterSpacing="3">
              FIRST FLOOR MAIN ACADEMIC CORRIDOR
            </text>

            {/* North Wing: Engineering Laboratories */}
            {renderRoomRect('CSE-Lab', 50, 50, 205, 165, 'CSE LABORATORY', 'Computing & AI Practical Lab')}
            {renderRoomRect('ME-Lab', 270, 50, 205, 165, 'ME LABORATORY', 'Mechanical Engineering Lab')}
            {renderRoomRect('ECE-Lab', 490, 50, 205, 165, 'ECE LABORATORY', 'Circuits & Embedded Systems Lab')}
            {renderRoomRect('IT-Lab', 710, 50, 200, 165, 'IT LABORATORY', 'Network & Cloud Systems Lab')}

            {/* South Wing: Theory Classrooms IET 17, 18, 19, 20 (~75 capacity each) */}
            {renderRoomRect('IET17', 50, 315, 205, 155, 'CLASSROOM IET 17', 'Tiered Theory Lecture Room')}
            {renderRoomRect('IET18', 270, 315, 205, 155, 'CLASSROOM IET 18', 'Smartboard Lecture Room')}
            {renderRoomRect('IET19', 490, 315, 205, 155, 'CLASSROOM IET 19', 'Theory Lecture Room')}
            {renderRoomRect('IET20', 710, 315, 200, 155, 'CLASSROOM IET 20', 'Theory Lecture Room')}
          </g>
        )}

        {/* ================= FLOOR 2: SECOND FLOOR ================= */}
        {floorNumber === 2 && (
          <g id="iet-second-floor">
            {/* Second Floor Corridor */}
            <rect x="50" y="235" width="860" height="60" fill="#F8FAFC" stroke="#CBD5E1" strokeDasharray="3 3" />
            <text x="480" y="270" fill="#94A3B8" fontSize="12" fontWeight="600" textAnchor="middle" letterSpacing="3">
              SECOND FLOOR CONCOURSE & SEMINAR CORRIDOR
            </text>

            {/* North Wing: Central Seminar Hall IET32 (~200 capacity) + IET24 */}
            {renderRoomRect('IET32', 50, 50, 580, 165, 'SEMINAR HALL IET 32', 'Auditorium & Major Conference Hall (Cap 200)')}
            {renderRoomRect('IET24', 650, 50, 260, 165, 'CLASSROOM IET 24', 'Lecture Classroom')}

            {/* South Wing: Classrooms IET 25, 28, 29, 30 (~75 capacity each) */}
            {renderRoomRect('IET25', 50, 315, 205, 155, 'CLASSROOM IET 25', 'Lecture Classroom')}
            {renderRoomRect('IET28', 270, 315, 205, 155, 'CLASSROOM IET 28', 'Lecture Classroom')}
            {renderRoomRect('IET29', 490, 315, 205, 155, 'CLASSROOM IET 29', 'Lecture Classroom')}
            {renderRoomRect('IET30', 710, 315, 200, 155, 'CLASSROOM IET 30', 'Lecture Classroom')}
          </g>
        )}

        {/* Map Legend */}
        <g transform="translate(40, 498)">
          <circle cx="10" cy="5" r="4" fill="#10B981" />
          <text x="20" y="9" fontSize="10" fill="#475569" fontWeight="500">Available</text>

          <circle cx="95" cy="5" r="4" fill="#EF4444" />
          <text x="105" y="9" fontSize="10" fill="#475569" fontWeight="500">Booked</text>

          <circle cx="165" cy="5" r="4" fill="#2563EB" />
          <text x="175" y="9" fontSize="10" fill="#475569" fontWeight="500">Selected</text>

          <circle cx="245" cy="5" r="4" fill="#F59E0B" />
          <text x="255" y="9" fontSize="10" fill="#475569" fontWeight="500">Pending</text>

          <circle cx="325" cy="5" r="4" fill="#6B7280" />
          <text x="335" y="9" fontSize="10" fill="#475569" fontWeight="500">Restricted</text>
        </g>
      </svg>
    </div>
  );
};

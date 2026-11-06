import React, { useState, useEffect } from 'react';
import { Building, Room } from '../../types';
import { api } from '../../services/api';
import { IETFloorMap } from './IETFloorMap';
import { DeekshaBhawanFloorMap } from './DeekshaBhawanFloorMap';
import { RoomDetailDrawer } from './RoomDetailDrawer';
import { Calendar, Clock, Layers, Building2, RefreshCw } from 'lucide-react';

interface FloorMapContainerProps {
  onBookRoom?: (room: Room) => void;
  userRole?: string;
}

export const FloorMapContainer: React.FC<FloorMapContainerProps> = ({ onBookRoom, userRole }) => {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [selectedBuildingId, setSelectedBuildingId] = useState<number>(1);
  const [selectedFloorNumber, setSelectedFloorNumber] = useState<number>(0);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Time & Date filter states
  const [targetDate, setTargetDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [targetTime, setTargetTime] = useState<string>('10:00');

  // Load buildings
  useEffect(() => {
    const loadBuildings = async () => {
      try {
        const bList = await api.getBuildings();
        setBuildings(bList);
        if (bList.length > 0) {
          setSelectedBuildingId(bList[0].id);
        }
      } catch (err) {
        console.error('Failed to load buildings', err);
      }
    };
    loadBuildings();
  }, []);

  // Fetch rooms with live availability for selected building, date & time
  const fetchRooms = async () => {
    setLoading(true);
    try {
      const roomList = await api.getRooms({
        building_id: selectedBuildingId,
        target_date: targetDate,
        target_time: targetTime,
      });
      setRooms(roomList);
      
      // Keep selectedRoom updated if drawer is open
      if (selectedRoom) {
        const updated = roomList.find((r) => r.id === selectedRoom.id);
        if (updated) setSelectedRoom(updated);
      }
    } catch (err) {
      console.error('Failed to load rooms', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedBuildingId) {
      fetchRooms();
    }
  }, [selectedBuildingId, targetDate, targetTime]);

  const activeBuilding = buildings.find((b) => b.id === selectedBuildingId);
  const isIET = activeBuilding?.code === 'IET';

  // Floor options for active building
  const floorOptions = isIET
    ? [
        { num: 0, label: 'Ground Floor (Library & Offices)' },
        { num: 1, label: 'First Floor (Labs & Classrooms 17-20)' },
        { num: 2, label: 'Second Floor (Seminar Hall 32 & 24-30)' },
      ]
    : [
        { num: 0, label: 'Ground Floor (LH 01 - 07)' },
        { num: 1, label: 'First Floor (LH 08 - 14)' },
      ];

  return (
    <div className="space-y-6">
      {/* Top Filter and Controls Bar */}
      <div className="bg-white p-4 md:p-5 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Building Selector */}
        <div className="flex items-center gap-2">
          {buildings.map((b) => {
            const isSelected = b.id === selectedBuildingId;
            return (
              <button
                key={b.id}
                onClick={() => {
                  setSelectedBuildingId(b.id);
                  setSelectedFloorNumber(0);
                  setSelectedRoom(null);
                }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-xs md:text-sm transition-all ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                }`}
              >
                <Building2 className="w-4 h-4" />
                <span>{b.code}</span>
                <span className="hidden sm:inline font-normal text-xs opacity-90">({b.name.split('(')[0].trim()})</span>
              </button>
            );
          })}
        </div>

        {/* Date, Time & Live Sync Pickers */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200">
            <Calendar className="w-4 h-4 text-slate-500" />
            <input
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              className="bg-transparent text-xs md:text-sm font-medium text-slate-700 focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-2 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200">
            <Clock className="w-4 h-4 text-slate-500" />
            <input
              type="time"
              value={targetTime}
              onChange={(e) => setTargetTime(e.target.value)}
              className="bg-transparent text-xs md:text-sm font-medium text-slate-700 focus:outline-none"
            />
          </div>

          <button
            onClick={fetchRooms}
            disabled={loading}
            title="Refresh availability"
            className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-600' : ''}`} />
          </button>
        </div>
      </div>

      {/* Floor Tab Selector */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 pl-1 pr-2">
          <Layers className="w-3.5 h-3.5" /> Floor:
        </span>
        {floorOptions.map((f) => {
          const isSelected = f.num === selectedFloorNumber;
          return (
            <button
              key={f.num}
              onClick={() => {
                setSelectedFloorNumber(f.num);
                setSelectedRoom(null);
              }}
              className={`px-4 py-2 rounded-xl text-xs md:text-sm font-medium transition-all shrink-0 ${
                isSelected
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'bg-white hover:bg-slate-50 text-slate-600 border border-slate-200'
              }`}
            >
              {f.label}
            </button>
          );
        })}
      </div>

      {/* Main Floor Map Canvas */}
      <div className="bg-white p-3 md:p-6 rounded-2xl border border-slate-200/80 shadow-sm">
        <div className="flex items-center justify-between mb-4 px-1">
          <div>
            <h3 className="font-bold text-slate-800 text-base md:text-lg flex items-center gap-2">
              {activeBuilding?.name}
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                Level {selectedFloorNumber}
              </span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Click any room to inspect facilities, real-time availability, and make bookings.
            </p>
          </div>
        </div>

        {isIET ? (
          <IETFloorMap
            floorNumber={selectedFloorNumber}
            rooms={rooms.filter((r) => r.floor_number === selectedFloorNumber)}
            selectedRoomId={selectedRoom?.id}
            onSelectRoom={(r) => setSelectedRoom(r)}
          />
        ) : (
          <DeekshaBhawanFloorMap
            floorNumber={selectedFloorNumber}
            rooms={rooms.filter((r) => r.floor_number === selectedFloorNumber)}
            selectedRoomId={selectedRoom?.id}
            onSelectRoom={(r) => setSelectedRoom(r)}
          />
        )}
      </div>

      {/* Slide-in Room Detail Drawer */}
      <RoomDetailDrawer
        room={selectedRoom}
        onClose={() => setSelectedRoom(null)}
        onBookRoom={onBookRoom}
        userRole={userRole}
      />
    </div>
  );
};

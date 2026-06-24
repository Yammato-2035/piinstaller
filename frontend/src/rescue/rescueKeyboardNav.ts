import { RESCUE_NAV_TILES, type RescueNavTileId } from './rescueNavTiles';

export const RESCUE_TILE_GRID_COLS = 2;

export function tileIndex(id: RescueNavTileId): number {
  return RESCUE_NAV_TILES.findIndex((t) => t.id === id);
}

export function tileIdAt(index: number): RescueNavTileId {
  const clamped = Math.max(0, Math.min(RESCUE_NAV_TILES.length - 1, index));
  return RESCUE_NAV_TILES[clamped].id;
}

export function moveTileFocus(
  current: RescueNavTileId,
  key: string,
  cols: number = RESCUE_TILE_GRID_COLS,
): RescueNavTileId | null {
  const idx = tileIndex(current);
  if (idx < 0) return null;
  const gridCols = Math.max(1, cols);
  const row = Math.floor(idx / gridCols);
  const col = idx % gridCols;
  const maxRow = Math.ceil(RESCUE_NAV_TILES.length / gridCols) - 1;

  switch (key) {
    case 'ArrowLeft':
      return col > 0 ? tileIdAt(idx - 1) : null;
    case 'ArrowRight':
      return col < gridCols - 1 && idx + 1 < RESCUE_NAV_TILES.length ? tileIdAt(idx + 1) : null;
    case 'ArrowUp':
      return row > 0 ? tileIdAt(idx - gridCols) : null;
    case 'ArrowDown':
      return row < maxRow && idx + gridCols < RESCUE_NAV_TILES.length ? tileIdAt(idx + gridCols) : null;
    case 'Home':
      return RESCUE_NAV_TILES[0].id;
    case 'End':
      return RESCUE_NAV_TILES[RESCUE_NAV_TILES.length - 1].id;
    default:
      return null;
  }
}

import { clientError } from './forms'

// Shared by trader locations and client saved addresses (name, address, optional coordinates).

export const PLACE_KEYS = ['name', 'address', 'latitude', 'longitude']

export const emptyPlace = () => ({ name: '', address: '', latitude: '', longitude: '' })

// Form values (all strings) from a server object.
export function placeToForm(place) {
  return {
    name: place?.name ?? '',
    address: place?.address ?? '',
    latitude: place?.latitude == null ? '' : String(place.latitude),
    longitude: place?.longitude == null ? '' : String(place.longitude),
  }
}

const blank = (v) => String(v ?? '').trim() === ''

function coordinateProblem(value, limit) {
  const n = Number(String(value).trim())
  if (!Number.isFinite(n) || Math.abs(n) > limit) return 'invalid'
  return ''
}

// field -> clientError(key). The server stays the authority; this only saves a round trip.
export function placeProblems(values) {
  const errors = {}
  const name = String(values.name ?? '').trim()
  const address = String(values.address ?? '').trim()
  if (!name) errors.name = clientError('places.errors.nameRequired')
  else if (name.length < 2) errors.name = clientError('places.errors.nameShort')
  if (!address) errors.address = clientError('places.errors.addressRequired')
  else if (address.length < 3) errors.address = clientError('places.errors.addressShort')
  const noLat = blank(values.latitude)
  const noLng = blank(values.longitude)
  if (noLat && !noLng) errors.latitude = clientError('places.errors.pairRequired')
  if (noLng && !noLat) errors.longitude = clientError('places.errors.pairRequired')
  if (!noLat && coordinateProblem(values.latitude, 90))
    errors.latitude = clientError('places.errors.latitudeInvalid')
  if (!noLng && coordinateProblem(values.longitude, 180))
    errors.longitude = clientError('places.errors.longitudeInvalid')
  return errors
}

// Request body: trimmed text and numbers, or both coordinates as null.
export function placePayload(values) {
  const hasCoords = !blank(values.latitude) && !blank(values.longitude)
  return {
    name: String(values.name).trim(),
    address: String(values.address).trim(),
    latitude: hasCoords ? Number(String(values.latitude).trim()) : null,
    longitude: hasCoords ? Number(String(values.longitude).trim()) : null,
  }
}

// A place chosen in an order form: one of the client's saved addresses, or one typed in.
export const emptyChoice = (hasSaved) => ({
  mode: hasSaved ? 'saved' : 'typed',
  savedId: '',
  place: emptyPlace(),
})

// field -> clientError(key); keys: savedId, name, address, latitude, longitude.
export function choiceProblems(choice) {
  if (choice.mode === 'saved')
    return choice.savedId ? {} : { savedId: clientError('places.errors.savedRequired') }
  return placeProblems(choice.place)
}

// The request fields for one side of an order: { [key]: place } or { [`${key}_saved_address`]: id }.
export function choicePayload(choice, key) {
  if (choice.mode === 'saved') return { [`${key}_saved_address`]: Number(choice.savedId) }
  return { [key]: placePayload(choice.place) }
}

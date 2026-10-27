import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { routes } from '@/router'
import TraderShopView from '@/views/TraderShopView.vue'
import TraderItemsView from '@/views/TraderItemsView.vue'
import { ApiError } from '@/api/http'
import * as shopApi from '@/api/shop'
import { plugins, signIn } from './helpers'

vi.mock('@/api/shop', async (orig) => ({
  ...(await orig()),
  getShop: vi.fn(),
  updateShop: vi.fn(),
  listItems: vi.fn(),
  createItem: vi.fn(),
  updateItem: vi.fn(),
  deleteItem: vi.fn(),
}))

const SHOP = {
  id: 1,
  name: 'Ahmed Store',
  phone: '01001234567',
  description: 'Pies',
  is_available: false,
  can_accept_orders: false,
}
const ITEMS = [
  { id: 8, name: 'Chicken wrap', description: '', is_hidden: true, price: null },
  { id: 7, name: 'Cheese pie', description: 'Warm', is_hidden: false, price: null },
]
const page = (results) => ({ count: results.length, next: null, previous: null, results })

async function open(view) {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  setActivePinia(pinia)
  signIn('trader')
  const w = mount(view, { global: { plugins: plugins([router], pinia) } })
  await flushPromises()
  return w
}

beforeEach(() => {
  vi.clearAllMocks()
  shopApi.getShop.mockResolvedValue({ ...SHOP })
  shopApi.listItems.mockResolvedValue(page(ITEMS))
})

describe('shop profile', () => {
  it('fills the form and explains a closed shop', async () => {
    const w = await open(TraderShopView)
    expect(w.find('#shop-name').element.value).toBe('Ahmed Store')
    expect(w.find('#shop-description').element.value).toBe('Pies')
    expect(w.find('[data-test="available"]').element.checked).toBe(false)
    expect(w.find('[data-test="why-closed"]').exists()).toBe(true)
  })

  it('explains a missing pickup location when the shop is open but not orderable', async () => {
    shopApi.getShop.mockResolvedValue({ ...SHOP, is_available: true })
    const w = await open(TraderShopView)
    expect(w.find('[data-test="why-pickup"]').exists()).toBe(true)
    expect(w.find('[data-test="why-pickup"] a').attributes('href')).toBe('/trader/locations')
  })

  it('says so when clients can order', async () => {
    shopApi.getShop.mockResolvedValue({ ...SHOP, is_available: true, can_accept_orders: true })
    const w = await open(TraderShopView)
    expect(w.find('[data-test="orderable-yes"]').exists()).toBe(true)
  })

  it('saves name, phone, description and availability, and shows the new state', async () => {
    shopApi.updateShop.mockResolvedValue({ ...SHOP, is_available: true, can_accept_orders: true })
    const w = await open(TraderShopView)
    await w.find('#shop-name').setValue('  New Name ')
    await w.find('[data-test="available"]').setValue(true)
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(shopApi.updateShop).toHaveBeenCalledWith({
      name: 'New Name',
      phone: '01001234567',
      description: 'Pies',
      is_available: true,
    })
    expect(w.find('[data-test="saved"]').exists()).toBe(true)
    expect(w.find('[data-test="orderable-yes"]').exists()).toBe(true)
  })

  it('allows an empty phone but blocks a bad one and an empty name', async () => {
    const w = await open(TraderShopView)
    await w.find('#shop-phone').setValue('12')
    await w.find('#shop-name').setValue('')
    await w.find('[data-test="form"]').trigger('submit')
    expect(shopApi.updateShop).not.toHaveBeenCalled()
    expect(w.find('#shop-phone-error').exists()).toBe(true)
    expect(w.find('#shop-name-error').exists()).toBe(true)
    await w.find('#shop-phone').setValue('')
    await w.find('#shop-name').setValue('Ok name')
    shopApi.updateShop.mockResolvedValue(SHOP)
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(shopApi.updateShop).toHaveBeenCalledTimes(1)
  })

  it('shows server errors on the field and keeps typed values', async () => {
    shopApi.updateShop.mockRejectedValue(
      new ApiError({ status: 400, errors: { name: ['Server says no.'] } }),
    )
    const w = await open(TraderShopView)
    await w.find('#shop-name').setValue('Another')
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(w.find('#shop-name-error').text()).toBe('Server says no.')
    expect(w.find('#shop-name').element.value).toBe('Another')
  })

  it('shows a retryable error when the load fails', async () => {
    shopApi.getShop.mockRejectedValueOnce(new ApiError({ status: 500 }))
    const w = await open(TraderShopView)
    expect(w.find('[data-test="load-error"]').exists()).toBe(true)
    await w.find('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(w.find('#shop-name').exists()).toBe(true)
  })
})

describe('shop items', () => {
  it('lists items, marks hidden ones, and has no price anywhere', async () => {
    const w = await open(TraderItemsView)
    const rows = w.findAll('[data-test="row"]')
    expect(rows).toHaveLength(2)
    expect(rows[0].find('[data-test="badge-hidden"]').exists()).toBe(true)
    expect(rows[1].find('[data-test="badge-hidden"]').exists()).toBe(false)
    expect(w.text().toLowerCase()).not.toContain('price:')
    await w.find('[data-test="add"]').trigger('click')
    expect(w.findAll('input').map((i) => i.attributes('name'))).toEqual(['name', 'description'])
  })

  it('shows the empty state', async () => {
    shopApi.listItems.mockResolvedValue(page([]))
    const w = await open(TraderItemsView)
    expect(w.find('[data-test="empty"]').exists()).toBe(true)
  })

  it('adds an item with trimmed text and reloads', async () => {
    shopApi.createItem.mockResolvedValue({ id: 9 })
    const w = await open(TraderItemsView)
    await w.find('[data-test="add"]').trigger('click')
    await w.find('#item-name').setValue('  Falafel ')
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(shopApi.createItem).toHaveBeenCalledWith({ name: 'Falafel', description: '' })
    expect(shopApi.listItems).toHaveBeenCalledTimes(2)
  })

  it('blocks an empty name and shows a duplicate-name error from the server', async () => {
    const w = await open(TraderItemsView)
    await w.find('[data-test="add"]').trigger('click')
    await w.find('[data-test="form"]').trigger('submit')
    expect(shopApi.createItem).not.toHaveBeenCalled()
    expect(w.find('#item-name-error').exists()).toBe(true)
    shopApi.createItem.mockRejectedValue(
      new ApiError({ status: 400, errors: { name: ['An item with this name already exists.'] } }),
    )
    await w.find('#item-name').setValue('Cheese pie')
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(w.find('#item-name-error').text()).toBe('An item with this name already exists.')
    expect(w.find('#item-name').element.value).toBe('Cheese pie')
  })

  it('edits an item with its values filled in', async () => {
    shopApi.updateItem.mockResolvedValue({ id: 7 })
    const w = await open(TraderItemsView)
    await w.findAll('[data-test="edit"]')[1].trigger('click')
    expect(w.find('#item-name').element.value).toBe('Cheese pie')
    await w.find('#item-description').setValue('Hot')
    await w.find('[data-test="form"]').trigger('submit')
    await flushPromises()
    expect(shopApi.updateItem).toHaveBeenCalledWith(7, { name: 'Cheese pie', description: 'Hot' })
  })

  it('hides and shows an item without deleting it', async () => {
    shopApi.updateItem.mockImplementation(async (id, body) => ({
      ...ITEMS.find((i) => i.id === id),
      ...body,
    }))
    const w = await open(TraderItemsView)
    await w.findAll('[data-test="toggle-hidden"]')[1].trigger('click')
    await flushPromises()
    expect(shopApi.updateItem).toHaveBeenCalledWith(7, { is_hidden: true })
    expect(w.findAll('[data-test="row"]')[1].find('[data-test="badge-hidden"]').exists()).toBe(true)
    await w.findAll('[data-test="toggle-hidden"]')[0].trigger('click')
    await flushPromises()
    expect(shopApi.updateItem).toHaveBeenCalledWith(8, { is_hidden: false })
    expect(shopApi.deleteItem).not.toHaveBeenCalled()
  })

  it('asks before deleting and removes the row', async () => {
    shopApi.deleteItem.mockResolvedValue()
    const w = await open(TraderItemsView)
    await w.findAll('[data-test="delete"]')[0].trigger('click')
    expect(shopApi.deleteItem).not.toHaveBeenCalled()
    await w.find('[data-test="confirm-yes"]').trigger('click')
    await flushPromises()
    expect(shopApi.deleteItem).toHaveBeenCalledWith(8)
    expect(w.findAll('[data-test="row"]')).toHaveLength(1)
  })

  it('shows a friendly error for a failed hide', async () => {
    shopApi.updateItem.mockRejectedValue(new ApiError({ status: 500 }))
    const w = await open(TraderItemsView)
    await w.findAll('[data-test="toggle-hidden"]')[0].trigger('click')
    await flushPromises()
    expect(w.find('[data-test="page-error"]').text()).toMatch(/went wrong/i)
  })

  it('routes exist for the trader area only', () => {
    const trader = routes.find((r) => r.path === '/trader')
    const names = trader.children.map((c) => c.name)
    expect(names).toEqual(expect.arrayContaining(['trader-shop', 'trader-items']))
  })
})

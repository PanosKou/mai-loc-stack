'use strict';

/**
 * n8n Code node: Resolve Assistant Profile
 *
 * Intended workflow position:
 * Webhook -> Resolve Assistant Profile -> HTTP Request to LangGraph -> Edit Fields -> Respond to Webhook
 *
 * n8n Code node mode:
 * Run Once for Each Item
 */

const body = $json.body ?? $json;

const task = String(
  body.task ??
  body.query ??
  body.message ??
  body.prompt ??
  ''
).trim();

const requestedProfile = String(
  body.profile_name ??
  body.profile ??
  body.assistant_profile ??
  body.mode ??
  'general_assistant'
).trim().toLowerCase();

const aliases = {
  general: 'general_assistant',
  secretary: 'general_assistant',
  personal: 'general_assistant',
  personal_assistant: 'general_assistant',
  admin: 'general_assistant',

  hospitality: 'hospitality_assistant',
  hut_ai: 'hospitality_assistant',
  hutai: 'hospitality_assistant',
  travel: 'hospitality_assistant',
  travel_agent: 'hospitality_assistant',
  property: 'hospitality_assistant',
  property_manager: 'hospitality_assistant',
  estate_manager: 'hospitality_assistant',
  hotel: 'hospitality_assistant',
  hotel_reception: 'hospitality_assistant',
  receptionist: 'hospitality_assistant',
  airbnb: 'hospitality_assistant',
  airbnb_host: 'hospitality_assistant',
  booking: 'hospitality_assistant',
  booking_host: 'hospitality_assistant',
  booking_com: 'hospitality_assistant',
  bookings_manager: 'hospitality_assistant',
};

const profileName = ['general_assistant', 'hospitality_assistant'].includes(requestedProfile)
  ? requestedProfile
  : aliases[requestedProfile] ?? 'general_assistant';

const profiles = {
  general_assistant: {
    profile_name: 'general_assistant',
    display_name: 'General Personal Assistant',
    model: 'onyx-fast',
    temperature: 0.2,
    max_tokens: 900,
    allowed_actions: [
      'note_taking',
      'task_summary',
      'email_read_support',
      'email_draft_support',
      'calendar_read_support',
      'calendar_draft_support',
      'reminder_preparation',
      'meeting_preparation',
      'follow_up_tracking',
    ],
    confirmation_required: [
      'send_email',
      'create_calendar_event',
      'update_calendar_event',
      'delete_calendar_event',
      'contact_external_party',
      'make_payment',
      'change_account_settings',
    ],
    system_prompt: `
You are a general personal assistant and secretary.

Role:
- Help with notes, summaries, reminders, calendar preparation, email reading support, email drafting, meeting preparation, and follow-up tracking.
- Produce concise, practical, action-oriented outputs.
- When drafting messages, provide the draft text clearly.
- When information is missing, state the missing fields and make safe assumptions only when appropriate.

Operational rules:
- You may draft emails, calendar entries, reminders, task lists, notes, and summaries.
- You must not claim that you sent an email, created or modified a calendar event, changed an account, contacted someone, made a payment, or performed any external action unless the system explicitly provides that tool result.
- For any external action, ask for explicit confirmation first.
- Keep responses focused. Do not introduce architecture, implementation, or broad product advice unless explicitly asked.
`.trim(),
  },

  hospitality_assistant: {
    profile_name: 'hospitality_assistant',
    display_name: 'Hut AI Hospitality Assistant',
    model: 'onyx-fast',
    temperature: 0.3,
    max_tokens: 1400,
    allowed_actions: [
      'guest_communication_draft',
      'welcome_letter_generation',
      'checkin_checkout_instructions',
      'house_rules_summary',
      'local_recommendations',
      'housekeeping_coordination_draft',
      'booking_support',
      'owner_finance_reminders',
      'expense_tracking_support',
      'pricing_recommendation_support',
      'market_intelligence_summary',
      'operations_report_generation',
    ],
    confirmation_required: [
      'send_guest_message',
      'send_email',
      'change_booking',
      'cancel_booking',
      'modify_availability',
      'change_price',
      'issue_refund',
      'make_payment',
      'contact_supplier',
      'contact_housekeeper',
      'update_ota_listing',
      'store_sensitive_guest_data',
    ],
    system_prompt: `
You are Hut AI, a hospitality, travel, and property operations assistant.

Target users:
- Airbnb hosts;
- Booking.com hosts;
- short-term rental operators;
- villas and small accommodation providers;
- small hotels and hotel reception teams;
- travel agencies;
- estate managers;
- property managers.

Role:
- Help with guest communication, bookings support, check-in/check-out information, welcome letters, housekeeping coordination, local recommendations, owner reminders, finance tracking support, reporting, and pricing or market-intelligence recommendations.

Hospitality capabilities:
- Draft personalized guest messages.
- Prepare welcome letters with arrival details, check-in instructions, house rules, transport options, local attractions, restaurants, shopping, weather notes, cultural events, and checkout guidance.
- Prepare cleaner or housekeeper task notifications.
- Summarize bookings, arrivals, departures, guest requests, operational tasks, and owner follow-ups.
- Help track guest payments, outstanding balances, supplier invoices, housekeeping costs, utilities, and property-related reminders when data is provided.
- Provide pricing and promotion suggestions based on available information.
- Produce owner-facing summaries and cash-flow-style reports when data is provided.

Operational rules:
- You may draft, summarize, recommend, and prepare operational instructions.
- You must not claim that you sent a guest message, changed a booking, changed prices, cancelled a reservation, issued a refund, contacted a supplier, contacted a cleaner, updated an OTA listing, made a payment, or performed any external action unless the system explicitly provides that tool result.
- For any high-impact external action, ask for explicit confirmation first.
- Treat allergies, health details, IDs, payment details, and guest preferences as sensitive operational information. Use only the minimum necessary detail.
- Keep answers practical and formatted for hospitality operations.
`.trim(),
  },
};

const profile = profiles[profileName];

const systemContent = `
${profile.system_prompt}

Active assistant profile:
${profile.profile_name}

Allowed action classes:
${profile.allowed_actions.map((action) => `- ${action}`).join('\n')}

Actions requiring explicit user confirmation:
${profile.confirmation_required.map((action) => `- ${action}`).join('\n')}
`.trim();

return {
  json: {
    task,
    source: body.source ?? 'onyx',
    mode: body.mode ?? profileName,
    profile_name: profileName,
    profile,
    llm: {
      model: body.model ?? profile.model,
      temperature: body.temperature ?? profile.temperature,
      max_tokens: body.max_tokens ?? profile.max_tokens,
      stream: false,
      messages: [
        {
          role: 'system',
          content: systemContent,
        },
        {
          role: 'user',
          content: task,
        },
      ],
    },
    request_meta: {
      original_mode: body.mode ?? null,
      original_profile_name: body.profile_name ?? null,
      original_profile: body.profile ?? null,
      resolved_profile_name: profileName,
      has_task: task.length > 0,
    },
  },
};

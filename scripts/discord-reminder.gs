/**
 * Sends a weekly meal planning reminder to Discord.
 *
 * Setup:
 * 1. Create a new Google Apps Script project at script.google.com
 * 2. Paste this script
 * 3. Go to Project Settings > Script Properties and add:
 *    - DISCORD_WEBHOOK_URL: your Discord channel webhook URL
 * 4. Go to Triggers (clock icon) > Add Trigger:
 *    - Function: sendMealPlanReminder
 *    - Event source: Time-driven
 *    - Type: Week timer
 *    - Day: Sunday
 *    - Time: 9am to 10am
 */

function sendMealPlanReminder() {
  var webhookUrl = PropertiesService.getScriptProperties().getProperty('DISCORD_WEBHOOK_URL');
  if (!webhookUrl) {
    throw new Error('DISCORD_WEBHOOK_URL not set in Script Properties');
  }

  var payload = {
    content: "🍳 Yo! Time to meal plan for the week.\nhttps://mkd-meal-planning-engine.streamlit.app/"
  };

  var options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload)
  };

  UrlFetchApp.fetch(webhookUrl, options);
}

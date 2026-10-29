# Discussion notes: EventTicket system architecture

## 1. System requirements

The system is a web application for discovering events, publishing them, and distributing tickets.

- **Visitors** can browse the application and view events.
- **Registered users** can view personal data, save favourite categories, receive related email notifications, view pre-sales and purchased tickets, book a pre-sale, buy a ticket, pay online, receive a ticket code, log out, and recover a forgotten password.
- **Managers** can view their proposed events, publish new events, view personal data, and log out.
- **Admins** can add managers, view personal data, and log out.

## 2. Architecture options discussed

### Layered monolith

One application handles the system. Code is arranged in technical layers, such as the web/API layer, business logic, and database access.

- **Advantages:** Simple to build, deploy, and run; can use a database transaction to coordinate related booking updates.
- **Disadvantages:** If organized only by technical layers, related features may be spread across the codebase. As the system grows, changes can become harder to manage.
- **Clarification:** It is not inherently worse than a modular monolith. For a small system, a well-organized layered monolith can work well.

### Modular monolith

One application is divided into feature modules, such as Accounts and Roles, Events, Ticketing, Payments, and Notifications. It can still use technical layers inside each module.

- **Advantages:** Keeps deployment relatively simple while making feature responsibilities clearer. Ticketing, for example, can own ticket availability and reservations.
- **Disadvantages:** The modules still run as one application and may share a database. Their boundaries need to be respected as the code changes.
- **Initial assessment:** A reasonable starting option for the requirements currently listed, subject to factors such as team size and expected traffic.

### Microservices

The system is split into separately deployed services, such as Accounts, Events, Ticketing, Payments, and Notifications. Services communicate over APIs or messages.

- **Advantages:** Services can be changed, deployed, and scaled independently. This can help a large system or teams working on separate areas.
- **Disadvantages:** There are more applications to build, configure, deploy, monitor, and troubleshoot. Network failures and keeping data consistent across services require extra handling. Ticketing and payment may need retries, timeouts, and compensation logic.
- **Initial assessment:** It may be useful if the system’s scale or team structure calls for independent services, but it adds complexity for the current scope.

## 3. Preventing two users from buying the last ticket

The architecture alone does not prevent overselling. Ticket availability needs one authoritative owner and an **atomic reservation**: when two buyers try to reserve the final ticket, only one request should succeed.

- In a **layered monolith**, booking logic can reserve the ticket in a database transaction.
- In a **modular monolith**, the Ticketing or Booking module can own the same transaction and prevent other modules from directly changing ticket availability.
- With **microservices**, a dedicated Ticketing or Inventory service should be the authority; other services must ask it to reserve a ticket.

A common flow is to hold a ticket temporarily while payment is processed. Successful payment confirms the ticket; failed or timed-out payment releases the hold. This prevents two buyers claiming the same ticket and avoids permanently tying up a ticket when payment fails.

## 4. Microservices and payment coordination

A microservice purchase may involve separate Ticketing and Payments services. For example, Ticketing might reserve the final ticket, then Payments might time out. The system needs to release the hold if payment fails, and make retries safe so the buyer is not charged twice.

A monolith can often coordinate booking updates in one database transaction. With microservices, these steps cross service boundaries, so the system needs explicit failure, retry, and reservation-release handling.

## 5. Decisions and open questions

- **No architecture has been selected yet.**
- A **modular monolith** is the tentative starting candidate based on the current requirements, since it offers clear feature boundaries without the operational overhead of multiple services.
- The choice could change depending on:
  - Expected numbers of users and events.
  - Team size and experience.
  - The payment provider and ticket-code validation process.
  - Whether notifications must be sent immediately or can be queued.
# Comparison Report: EventTicket ADR With and Without a Skill

## Results

Compared the ADR created without the Skill (EventTicket-ADR-001.md) with the ADR created using the Skill (ADR-001-event-ticketing-architecture.md).

Both results are quite similar in the main decision. They compare three architectures: Layered Monolith, Modular Monolith, and Microservices. Both recommend a **Modular Monolith** for EventTicket and explain why it is a good choice. They also include a comparison table, an architecture diagram, and possible risks.

The main difference is the amount of detail. The ADR created **with the Skill** explains some parts more deeply, especially payment failures, ticket reservations, notifications, and security. It also includes more assumptions and open questions. The ADR created **without the Skill** is shorter and easier to read. So the difference in the final answer is noticeable, but not huge: both documents cover the important points and reach the same conclusion.

## Time Comparison

| Method | Approximate time |
|---|---|
| Without Skill | 2 min 30 sec |
| With Skill | 1 min 40 sec |

Using the Skill saved about **50 seconds**, which is roughly **33% less time**. The times are approximate measurements from my sessions.

## Conclusion

In my opinion, the Skill was useful. It helped me get a slightly more detailed ADR in less time, without having to explain all the expected sections again. However, it did not change the architecture choice or make the result completely different. The biggest improvement was the faster and more straightforward process.

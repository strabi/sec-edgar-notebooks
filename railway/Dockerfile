# syntax=docker/dockerfile:1.7

# Custom Neo4j image that restores the full SEC EDGAR dump on startup.
# Railway builds this image and runs it with the same environment variables
# you use locally (auth, APOC flags, etc.).

FROM neo4j:5.23.0

# Copy the dump into the image build context so the container can restore it.
# The dump comes from the repository's data/sample directory.
COPY data/sample/neo4j.dump /imports/neo4j.dump

# Copy helper script that restores the dump (only on first boot) and then
# chains to the stock Neo4j entrypoint.
COPY railway/restore-and-run.sh /startup/restore-and-run.sh
RUN chmod +x /startup/restore-and-run.sh

ENTRYPOINT ["/bin/bash", "/startup/restore-and-run.sh"]
CMD ["neo4j"]

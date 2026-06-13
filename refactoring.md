# discussion about engines/document/models and engines as services/docker services

1. some models are engine specific models such as ksdm, osdm, tsdm, so the model and writers and parsers need to be in the folder structure that I already mentioned near its engine.
2. some folders in the system are libraries that can be used in different engines. these are normally client libraries for bus communication or service endpoints for interpocess communications and state management and event communication and connecting to storage providers such as sql/nosql/time based databases and etcd/redis key/value and state storages an also file storage...
3. msdm is a shared library, there are two ways:
3.1 Way1: Msdm parsers and writers also can be shared libraries near the model definition, the storage service and location for msdm models can be defined in system configurations.
3.2 Way2 we can consider one of engines such as knowledge engine to serve the msdm/ontology to the other services. in this way madm parsers and writers need to be inside this engine. but because the other engines also require msdm models, we need to provide tools for communicating and also syncing msdm model registries to the other engines.
4. lsdm used by knowledge/context engines as a readonly tools and in other engines as a write only tools. so I think the lsdm models and its parsers ad writers and registries can be shared libraries.
5. csdm, esdm, psdm, usdm models are defined for business/context documents. again the models can be shared libraries or completely inside document engine.
6. dsdm models are used in ssdm (that we will discuss later), as document formats (such as other esdm, psdm, usdm, csdm models).
7. ssdm model defines several communication aspects, it maybe need to be separated or can be a shared model. but can not be a shared/single/central rpository.
7.1 Internal system communicaions such as message/event formats and service contracts need to be defined and sahred between the engines and dockers using that messages/events/service contracts (not the other engines). 
7.2 Ssdm models for the exposure layer (API gateway is used only for its engine so it requires its own registry). 
7.3 Also for consuming services we can have tools layer, this tool layer can be considered as a separate service/docker. this service docker can be as a proxy to the other systems/tools/services proxy to our system, we also will provide an MCP for this service tools.

So one way is separating ssdm models as different models for 
- internal communcaions (message busses, queues, k/v state databases, event communications, grpc contracts, service and microservices definitions, etc) as issdm, 
- system service exposures (essdm models) we can have several services endpoints such as API gateway and MCP server for the system and different protocols such as rest, grpc, A2A, ... 
- system service consumption (cssdm) the service consumption tools engine can have its own repository.

The above services have their own repositories and the definition models have many similarities; Also probably similar protocols. but also have some specific definitions that only mean for exlusive use so essdm, cssdm, issdm models can be different, isdm models and communication tools for internal communications must be shared but essdm and cssdm models, parsers, writers and reposotories and protocols/engines for API gateway and consumption layer can be inside their layers. 

There is a question for the best location for issdm repository, because it is important that id a communication definition between service A and B is changed, it must not force the service C to recompiled/reloaded.

8. agent layer will remain in python and agent, skill, mcp contracts, tools definition models and their parsers/writers and engines must be inside it.
9. orchestration layer may be one or multiple engines, osdm models have some shared objects, but there are some engine specific models (DMN/ CMMP, CEP, State machine, BPMN, bam, ...), these models and their parsers and writers codes must be separated and moved near their engines, also api layer seams to be required to move to api gateway engine. 
10. knowledge layer also contains several engines, we consider it now as a single service, but it is several relatively independent sevices, their models readers and writers need to be moved near these engines.
11. tools folder also contains several adapters, each can be assumed as a seperate service/docker in our microservices platform, but curently we consider it as a single layer, so tsdm model and writers and parsers need to be moved inside this folder 
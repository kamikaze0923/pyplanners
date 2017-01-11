from set_additive import *
from ff import *
from set_additive import applicable as sa_applicable, first_goals as sa_first_goals, \
  first_operators as sa_first_operators, first_combine as sa_first_combine
from planner.main import default_plan, simple_debug
from planner.progression import *

def h_0(state, goal, operators): return 0
def h_naive(state, goal, operators): return sum(1 for var, value in goal.cond() if state[var] != value)
def h_blind(state, goal, operators): return min(operator.cost for operator in ha_applicable(state, goal, operators))

###########################################################################

def ha_all(state, goal, operators): return filter_axioms(operators)
def ha_applicable(state, goal, operators): return filter_axioms([operator for operator in operators if operator(state) is not None])
def ha_all_random(state, goal, operators): return randomize(ha_all(state, goal, operators))
def ha_applicable_random(state, goal, operators): return randomize(ha_applicable(state, goal, operators))
def ha_sorted(state, goal, operators): return sorted(ha_applicable(state, goal, operators), key=lambda o: o.cost)

def ha_combine(state, goal, operators, *helpful_actions):
  seen_operators = set()
  for ha in helpful_actions:
    ha_operators = []
    for operator in ha(state, goal, operators):
      if not in_add(seen_operators, operator):
        ha_operators.append(operator)
    yield ha_operators

###########################################################################

def combine(heuristic, helpful_actions):
  return lambda s, g, o: (heuristic(s, g, o), helpful_actions(s, g, o))

def single_complete_ff(ff):
  def fn(state, goal, operators):
    h, ha = ff(state, goal, operators)
    return h, ha + list(set(ha_applicable(state, goal, operators)) - set(ha))
  return fn

def multi_complete_ff(ff):
  def fn(state, goal, operators):
    h, ha = ff(state, goal, operators)
    yield h, ha
    yield h, set(ha_applicable(state, goal, operators)) - set(ha)
  return fn

# TODO - the original operator order is affecting things a lot
# NOTE - expensive to do sa for many successsors (the union operation)
#default_successors = combine(h_0, ha_applicable_random)
#default_successors = combine(h_level, ha_applicable_random)
#default_successors = combine(h_sa, ha_applicable_random)
default_successors = ff_fn(plan_cost, first_combine, op=sum)
#default_successors = sa_fn(sa_first_operators) # sa_first_goals | sa_first_operators | sa_first_combine

###########################################################################

def single_generator(initial, goal, operators, successors):
  #return lambda v: (yield successors(v.state, goal, operators))
  return lambda v: iter([successors(v.state, goal, operators)])

def multi_generator(initial, goal, operators, successors):
  return lambda v: iter(successors(v.state, goal, operators))

default_generator = lambda i, g, o: single_generator(i, g, o, default_successors)

###########################################################################

from downward import *
from collections import OrderedDict

class Problem(object):
  def __init__(self, initial, goal, actions, axioms):
    self.var_indices = {}
    self.var_order = []
    self.var_val_indices = {}
    self.var_val_order = {}
    self.actions = []
    self.mutexes = []
    self.costs = True

    for var, val in initial.values.iteritems():
      self.add_val(var, val)
    for var, val in goal.conditions.iteritems():
      self.add_val(var, val)
    for action in actions:
      self.add_action(action)

    for var in self.var_order:
      print var
      print self.var_val_order[var]
      print

  def add_var(self, var):
    if var not in self.var_indices:
      self.var_indices[var] = len(self.var_order)
      self.var_order.append(var)
      self.var_val_indices[var] = {}
      self.var_val_order[var] = []

  def add_val(self, var, val):
    self.add_var(var)
    if val not in self.var_val_indices[var]:
      self.var_val_indices[var][val] = len(self.var_val_order[var])
      self.var_val_order[var].append(val)

  def add_action(self, action):
    self.actions.append(action)
    for var, val in action.conditions.iteritems():
      self.add_val(var, val)
    for var, val in action.effects.iteritems():
      self.add_val(var, val)

  def get_var(self, var):
    return self.var_indices[var]


def downward_plan(initial, goal, operators):
  print initial
  print
  #print goal
  #print operators

  problem = Problem(initial, goal, operators, [])

  return None, None

###########################################################################

#default_search = default_plan
#default_search = lambda initial, goal, generator: bfs(initial, goal, generator, INF, INF, INF, INF, INF, None)
#default_search = lambda initial, goal, generator: a_star_search(initial, goal, generator,
#        lambda v: v.cost, False, INF, INF, INF, INF, INF, None)
#default_search = lambda initial, goal, generator: a_star_search(initial, goal, generator,
#        lambda v: v.cost + v.h_cost, True, INF, INF, INF, INF, INF, None)
#default_search = lambda initial, goal, generator: best_first_search(initial, goal, generator,
#        lambda v: v.h_cost, False, INF, INF, INF, INF, INF, None)
default_search = lambda initial, goal, generator: deferred_best_first_search(initial, goal, generator,
        lambda v: v.h_cost, False, INF, INF, INF, INF, INF, None) # True vs False can matter quite a bit
#default_search = lambda initial, goal, generator: semideferred_best_first_search(initial, goal, generator,
#        lambda v: v.h_cost, True, INF, INF, INF, INF, INF, None) # True vs False can matter quite a bit
#default_search = lambda initial, goal, generator: hill_climbing_search(initial, goal, generator,
#        None, 0, 1, False, INF, INF, INF, INF, INF, None)

def default_plan(initial, goal, operators):
  return default_search(initial, goal, default_generator(initial, goal, operators))

def default_derived_plan(initial, goal, operators, axioms):
  return default_search(initial, goal, (lambda v: iter([default_successors(v.state, goal, operators + axioms)]), axioms))

default_plan = downward_plan